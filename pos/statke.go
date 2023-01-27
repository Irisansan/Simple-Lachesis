package pos

import (
	"Lachesis/inputs"
)

// WeightCounter counts weights.
type WeightCounter struct {
	validators Validators
	already    map[inputs.ValidatorId]bool // ValidatorId -> bool
	sum        Weight
}

// NewCounter constructor.
func (vv Validators) NewCounter() *WeightCounter {
	return newWeightCounter(vv)
}
func newWeightCounter(vv Validators) *WeightCounter {
	return &WeightCounter{
		validators: vv,
		already:    make(map[inputs.ValidatorId]bool),
		sum:        0,
	}
}

// Count validator and return true if it hadn't counted before.
func (s *WeightCounter) Count(v inputs.ValidatorId) bool {
	if s.already[v] {
		return false
	}
	s.already[v] = true
	s.sum += s.validators.GetWeightById(v)
	return true
}

func (s *WeightCounter) SumWeight() Weight { return s.sum }
