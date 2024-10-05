use anyhow::Result;
use clap::{Parser, ValueEnum};

#[derive(Debug, Clone, ValueEnum, PartialEq)]
#[clap(rename_all = "kebab_case")]
enum PrintOption {
    Shrink,
    All,
    None,
}

impl std::fmt::Display for PrintOption {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        f.write_str(&format!("{:?}", self).to_ascii_lowercase())
    }
}

#[derive(clap::Parser)]
#[command(version = concat!(env!("CARGO_PKG_VERSION"), " ", env!("PROFILE")))]
struct CliArgs {
    #[arg(long, default_value_t = String::from("${genvmRoot}/share/genvm/default-config.json"))]
    config: String,
    #[arg(long)]
    message: String,
    #[arg(long)]
    host: String,
    #[clap(long, default_value_t = PrintOption::None)]
    print: PrintOption,
}

fn main() -> Result<()> {
    let args = CliArgs::parse();

    let message: genvm::MessageData = serde_json::from_str(&args.message)?;

    let host = genvm::Host::new(&args.host)?;
    let supervisor = genvm::create_supervisor(&args.config, message.gas, host)?;
    let res = genvm::run_with(message, supervisor);
    let res: Option<String> = match (res, args.print) {
        (_, PrintOption::None) => None,
        (Err(e), PrintOption::Shrink) => {
            eprintln!("shrinked error {:?}", e);
            Some("Error(\"\")".into())
        }
        (Err(e), _) => Some(format!("Error({})", e)),
        (Ok(res), _) => Some(format!("{:?}", &res)),
    };
    match res {
        None => {}
        Some(res) => println!("executed with `{res}`"),
    }
    // FIXME exit code?
    Ok(())
}