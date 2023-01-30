package pos

import (
	"Lachesis/idx"
)

type Weight uint32

type Validators struct {
	validator   map[idx.ValidatorId]Weight
	weight      []Weight
	branch      []idx.ValidatorId
	totalWeight Weight
}

// NewValidator build a new validator
func (vv *Validators) NewValidator(id idx.ValidatorId, w Weight) {
	if vv.validator == nil {
		vv.validator = make(map[idx.ValidatorId]Weight)
	}
	vv.validator[id] = w

	ww := append(vv.weight, w)
	vv.weight = ww
	ids := append(vv.branch, id)
	vv.branch = ids

	var total Weight = 0
	for _, v := range vv.weight {
		total += v
	}
	vv.totalWeight = total
}

func (vv *Validators) TotalWeight() Weight                   { return vv.totalWeight }
func (vv *Validators) Branch() []idx.ValidatorId             { return vv.branch }
func (vv *Validators) Validator() map[idx.ValidatorId]Weight { return vv.validator }
func (vv *Validators) Weight() []Weight                      { return vv.weight }

func (vv *Validators) GetWeightById(v idx.ValidatorId) Weight { return vv.validator[v] }

// Quorum limit of validators.
func (vv *Validators) Quorum() Weight {
	return vv.TotalWeight()*2/3 + 1
}
