use std::{collections::BTreeMap, str::FromStr, sync::Arc};

use crate::common::{ModuleResult, ModuleResultUserError};
use anyhow::Context;
use genvm_modules_interfaces::llm as llm_iface;
use mlua::{LuaSerdeExt, UserDataRef};
use serde::{Deserialize, Serialize};

use super::{
    config,
    handler::{self, LuaError},
    prompt::{self, ImageLua, ImageType},
};

pub struct UserVM {
    vm: mlua::Lua,
    exec_prompt: mlua::Function,
    exec_prompt_template: mlua::Function,
}

#[derive(Serialize)]
struct Greyboxing {
    available_backends: BTreeMap<String, config::ScriptBackendConfig>,
    templates: serde_json::Value,
}

#[derive(Serialize)]
enum LuaReturn {
    Ok(llm_iface::PromptAnswer),
    Err(serde_json::Value),
}

impl mlua::UserData for handler::Handler {
    fn add_methods<M: mlua::UserDataMethods<Self>>(methods: &mut M) {
        #[derive(Deserialize)]
        struct Args {
            provider: String,
            prompt: prompt::Internal,
            format: prompt::ExtendedOutputFormat,
            model: String,
        }

        async fn exec_in_backend(
            vm: mlua::Lua,
            args: (mlua::AnyUserData, mlua::Value),
        ) -> Result<mlua::Value, mlua::Error> {
            let (zelf, args) = args;
            let zelf: UserDataRef<Arc<handler::Handler>> =
                zelf.borrow().with_context(|| "unboxing userdata")?;

            let args: Args = vm
                .from_value(args)
                .with_context(|| "deserializing arguments")?;

            let res = zelf
                .exec_prompt_in_provider(&args.prompt, &args.model, &args.provider, args.format)
                .await
                .with_context(|| "running in provider");

            let res = match res {
                Ok(res) => LuaReturn::Ok(res),
                Err(e) => {
                    let as_lua_err = match e.downcast::<LuaError>() {
                        Ok(lua_err) => lua_err,
                        Err(other_err) => LuaError {
                            kind: handler::LuaErrorKind::Internal,
                            context: serde_json::json!({
                                "error_message": format!("{other_err:#}"),
                            }),
                        },
                    };

                    LuaReturn::Err(
                        serde_json::to_value(&as_lua_err)
                            .map_err(|e| mlua::Error::ExternalError(Arc::new(e)))?,
                    )
                }
            };

            vm.to_value_with(&res, DEFAULT_LUA_SER_OPTIONS)
        }
        methods.add_async_function("exec_in_backend", exec_in_backend);
    }
}

const DEFAULT_LUA_SER_OPTIONS: mlua::SerializeOptions = mlua::SerializeOptions::new()
    .serialize_none_to_null(false)
    .serialize_unit_to_null(false);

impl UserVM {
    pub fn new(config: &config::Config) -> anyhow::Result<Arc<UserVM>> {
        use mlua::StdLib;

        let lua_lib_path = {
            let mut lua_lib_path = std::env::current_exe()?;
            lua_lib_path.pop();
            lua_lib_path.pop();
            lua_lib_path.push("share");
            lua_lib_path.push("lib");
            lua_lib_path.push("genvm");
            lua_lib_path.push("greyboxing");

            let mut path = lua_lib_path
                .to_str()
                .ok_or_else(|| anyhow::anyhow!("could not detect default lib path"))?
                .to_owned();
            path.push_str("/?.lua");

            path
        };

        std::env::set_var("LUA_PATH", &lua_lib_path);

        let lua_libs = StdLib::COROUTINE
            | StdLib::TABLE
            | StdLib::IO
            | StdLib::STRING
            | StdLib::MATH
            | StdLib::PACKAGE;

        let vm = mlua::Lua::new_with(lua_libs, mlua::LuaOptions::default())?;

        vm.globals().set("LUA_PATH", lua_lib_path)?;

        vm.load_std_libs(lua_libs)?;

        let greyboxing = Greyboxing {
            available_backends: config
                .backends
                .iter()
                .map(|(k, v)| (k.clone(), v.script_config.clone()))
                .collect(),
            templates: serde_json::to_value(&config.prompt_templates)?,
        };

        let greyboxing = vm.to_value_with(&greyboxing, DEFAULT_LUA_SER_OPTIONS)?;
        let log_fn = vm.create_function(|vm: &mlua::Lua, data: mlua::Value| {
            let mut as_serde: BTreeMap<String, LogValue> = vm.from_value(data)?;

            let level = as_serde.remove("level");
            let level = level.and_then(|x| x.as_str().map(|x| x.to_owned())).map(|x| log::Level::from_str(&x).unwrap_or(log::Level::Info)).unwrap_or(log::Level::Info);

            let script_message = as_serde.remove("message").and_then(|x| x.as_str().map(|x| x.to_owned())).unwrap_or_else(|| "<none>".to_owned());

            log::log!(level, log:serde = as_serde, cookie = crate::common::get_cookie(); "script_log: {script_message}");
            Ok(())
        })?;

        greyboxing.as_table().unwrap().set("log", log_fn)?;

        let sleep_fn = vm.create_async_function(|vm: mlua::Lua, data: mlua::Value| async move {
            let as_seconds: f32 = vm.from_value(data)?;
            tokio::time::sleep(tokio::time::Duration::from_secs_f32(as_seconds)).await;
            Ok(())
        })?;

        greyboxing
            .as_table()
            .unwrap()
            .set("sleep_seconds", sleep_fn)?;

        vm.globals().set("greyboxing", greyboxing)?;

        let user_script = std::fs::read_to_string(&config.lua_script_path)
            .with_context(|| format!("reading {}", config.lua_script_path))?;

        let chunk = vm.load(user_script);
        chunk.exec()?;

        let exec_prompt: mlua::Function = vm
            .globals()
            .get("exec_prompt")
            .with_context(|| "getting exec_prompt")?;

        let exec_prompt_template: mlua::Function = vm
            .globals()
            .get("exec_prompt_template")
            .with_context(|| "getting exec_prompt_template")?;

        log::info!("lua VM initialized");

        Ok(Arc::new(UserVM {
            vm,
            exec_prompt,
            exec_prompt_template,
        }))
    }

    pub async fn greybox(
        &self,
        handler: Arc<handler::Handler>,
        payload: &llm_iface::PromptPayload,
    ) -> ModuleResult<llm_iface::PromptAnswer> {
        let host_data = self
            .vm
            .to_value_with(&handler.hello.host_data, DEFAULT_LUA_SER_OPTIONS)?;

        let handler = mlua::Value::UserData(self.vm.create_userdata(handler)?);

        let images: anyhow::Result<Vec<mlua::Value>> = payload
            .images
            .iter()
            .map(|v| {
                let kind = ImageType::sniff(&v.0).ok_or(ModuleResultUserError(
                    serde_json::json!("can't sniff image type. only png and jpg are supported"),
                ))?;
                let as_arc = Arc::new(ImageLua {
                    data: v.0.clone(),
                    kind,
                });
                Ok(mlua::Value::UserData(
                    self.vm.create_ser_any_userdata(as_arc)?,
                ))
            })
            .collect();

        let images = images?;

        let payload = self.vm.create_table_from([
            (
                "response_format",
                self.vm
                    .to_value_with(&payload.response_format, DEFAULT_LUA_SER_OPTIONS)?,
            ),
            (
                "prompt",
                self.vm
                    .to_value_with(&payload.prompt, DEFAULT_LUA_SER_OPTIONS)?,
            ),
            (
                "images",
                self.vm.to_value_with(&images, DEFAULT_LUA_SER_OPTIONS)?,
            ),
        ])?;

        let arg = self.vm.create_table_from([
            ("handler", handler),
            ("payload", mlua::Value::Table(payload)),
            ("host_data", host_data),
        ])?;

        let res: mlua::Value = self
            .exec_prompt
            .call_async(arg)
            .await
            .with_context(|| "calling user script")?;
        let res = self.vm.from_value(res)?;

        Ok(res)
    }

    pub async fn greybox_template(
        &self,
        handler: Arc<handler::Handler>,
        payload: llm_iface::PromptTemplatePayload,
    ) -> ModuleResult<llm_iface::PromptAnswer> {
        let host_data = self
            .vm
            .to_value_with(&handler.hello.host_data, DEFAULT_LUA_SER_OPTIONS)?;

        let handler = self.vm.create_userdata(handler)?;
        let handler: mlua::Value = mlua::Value::UserData(handler);
        let payload = self.vm.to_value_with(&payload, DEFAULT_LUA_SER_OPTIONS)?;

        let arg = self.vm.create_table_from([
            ("handler", handler),
            ("payload", payload),
            ("host_data", host_data),
        ])?;

        let res: mlua::Value = self
            .exec_prompt_template
            .call_async(arg)
            .await
            .with_context(|| "calling user script")?;
        let res = self.vm.from_value(res)?;

        Ok(res)
    }
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(untagged)]
pub enum LogValue {
    Null,
    Bool(bool),
    Str(String),
    Bytes(#[serde(with = "serde_bytes")] Vec<u8>),
    Number(f64),
    Map(BTreeMap<String, LogValue>),
    Array(Vec<LogValue>),
}

impl LogValue {
    pub fn as_str(&self) -> Option<&str> {
        match self {
            LogValue::Str(s) => Some(s),
            _ => None,
        }
    }
}
