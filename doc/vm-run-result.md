# What is a vm exectuion result?

1. Success --- calldata-encoded data that contract provided
2. Rollback --- error that a guest program explicitly produced and can handle
3. Contract error --- error that a guest program caused (i.e. non-zero exit code) and can't handle
4. Error --- unrecoverable error that makes entire transaction to not be applied ; internal vm failure

Solidity states following about rollback (revert):

> A failure in an external call can be caught using a try/catch statement

> the caller can react on such failures using try/catch, but the changes in the callee will always be reverted.

What is different in GenVM?
1. Nondeterministic blocks are akin to external function calls
2. Contract calls can't modify state
3. Nondeterministic blocks can't modify state
