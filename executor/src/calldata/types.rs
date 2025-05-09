use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

pub const ADDRESS_SIZE: usize = 20;

#[derive(Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Hash)]
pub struct Address(pub(super) [u8; ADDRESS_SIZE]);

impl std::fmt::Debug for Address {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_fmt(format_args!("\"0x{}\"", hex::encode(self.0)))
    }
}

impl Address {
    pub const fn from(raw: [u8; ADDRESS_SIZE]) -> Self {
        Self(raw)
    }

    pub fn raw(self) -> [u8; ADDRESS_SIZE] {
        self.0
    }

    pub fn ref_mut(&mut self) -> &mut [u8; ADDRESS_SIZE] {
        &mut self.0
    }

    pub const fn zero() -> Self {
        Self([0; 20])
    }

    pub const fn len() -> usize {
        20
    }
}

#[derive(Debug, Clone)]
pub enum Value {
    Null,
    Address(Address),
    Bool(bool),
    Str(String),
    Bytes(Vec<u8>),
    Number(num_bigint::BigInt),
    Map(BTreeMap<String, Value>),
    Array(Vec<Value>),
}
