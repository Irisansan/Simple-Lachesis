package lachesis

type Validators map[uint32]Validator

type Validator struct {
	weight uint32
}
