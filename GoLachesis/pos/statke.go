package pos

import (
	"Lachesis/idx"
)

// WeightCounter counts weights.
type WeightCounter struct {
	validators Validators
	already    map[idx.ValidatorId]bool // ValidatorId -> bool
	quorum     Weight
	sum        Weight
}

// NewCounter constructor.
func (vv Validators) NewCounter() *WeightCounter {
	return newWeightCounter(vv)
}
func newWeightCounter(vv Validators) *WeightCounter {
	return &WeightCounter{
		validators: vv,
		already:    make(map[idx.ValidatorId]bool),
		quorum:     vv.Quorum(),
		sum:        0,
	}
}

// Count validator and return true if it hadn't counted before.
func (s *WeightCounter) Count(v idx.ValidatorId) bool {
	if s.already[v] {
		return false
	}
	s.already[v] = true
	s.sum += s.validators.GetWeightById(v)
	return true
}

func (s *WeightCounter) SumWeight() Weight { return s.sum }

// HasQuorum achieved.
func (s *WeightCounter) HasQuorum() bool {
	return s.sum >= s.quorum
}
