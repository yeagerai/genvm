use serde_derive::Serialize;
#[derive(PartialEq, Clone, Copy, Serialize)]
#[repr(u8)]
pub enum ResultCode {
    Return = 0,
    Rollback = 1,
    ContractError = 2,
    Error = 3,
}

#[allow(dead_code)]
impl ResultCode {
    pub fn str_snake_case(self) -> &'static str {
        match self {
            ResultCode::Return => "return",
            ResultCode::Rollback => "rollback",
            ResultCode::ContractError => "contract_error",
            ResultCode::Error => "error",
        }
    }
}

impl TryFrom<u8> for ResultCode {
    type Error = ();

    fn try_from(value: u8) -> Result<Self, ()> {
        match value {
            0 => Ok(ResultCode::Return),
            1 => Ok(ResultCode::Rollback),
            2 => Ok(ResultCode::ContractError),
            3 => Ok(ResultCode::Error),
            _ => Err(()),
        }
    }
}
#[derive(PartialEq, Clone, Copy, Serialize)]
#[repr(u8)]
pub enum StorageType {
    Default = 0,
    LatestFinal = 1,
    LatestNonFinal = 2,
}

#[allow(dead_code)]
impl StorageType {
    pub fn str_snake_case(self) -> &'static str {
        match self {
            StorageType::Default => "default",
            StorageType::LatestFinal => "latest_final",
            StorageType::LatestNonFinal => "latest_non_final",
        }
    }
}

impl TryFrom<u8> for StorageType {
    type Error = ();

    fn try_from(value: u8) -> Result<Self, ()> {
        match value {
            0 => Ok(StorageType::Default),
            1 => Ok(StorageType::LatestFinal),
            2 => Ok(StorageType::LatestNonFinal),
            _ => Err(()),
        }
    }
}
