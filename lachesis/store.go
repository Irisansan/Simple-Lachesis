package lachesis

import (
	"Lachesis/dag"
	"Lachesis/idx"
	"Lachesis/pos"
)

type Roots []dag.Event
type Frames []Roots

// Store all events, validators and the frames including roots
type Store struct {
	events     dag.Events
	validators pos.Validators
	frames     Frames
	Atropos
}

func (s *Store) StoreEvents(events dag.Events)     { s.events = events }
func (s *Store) StoreValidators(vv pos.Validators) { s.validators = vv }
func (s *Store) StoreFrames(frame idx.Frame, root dag.Event) {
	var r = Roots{}
	if s.frames == nil {
		r = make(Roots, 4)
		s.frames = make(Frames, 10)
	} else {
		r = s.frames[frame]
	}
	r = append(s.frames[frame], root)
	s.frames[frame] = r
}

func (s *Store) Events() dag.Events          { return s.events }
func (s *Store) Validators() pos.Validators  { return s.validators }
func (s *Store) Roots(frame idx.Frame) Roots { return s.frames[frame] }
func (s *Store) Frames() Frames              { return s.frames }
