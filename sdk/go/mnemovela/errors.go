package mnemovela

import "fmt"

// MnemeError represents a JSON-RPC error object or a transport failure.
type MnemeError struct {
	Code    int
	Message string
}

func (e *MnemeError) Error() string { return fmt.Sprintf("%d: %s", e.Code, e.Message) }
