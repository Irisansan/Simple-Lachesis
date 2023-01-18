package lachesis

type Validators map[uint32]Validator

type Validator struct {
	weight uint32
}

func (v *Validator) Weight() uint32     { return v.weight }
func (v *Validator) SetWeight(w uint32) { v.weight = w }

func TotalWeight(v Validators) uint32 {
	var total uint32 = 0
	for _, w := range v {
		total += w.Weight()
	}
	return total
}
