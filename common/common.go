package common

import (
	"Lachesis/inputs"
	"fmt"
	"strconv"
)

func StringToUint32(s string) uint32 {
	ui64, err := strconv.ParseUint(s, 10, 64)
	if err != nil {
		fmt.Println("Errors about StringToUint")
		panic(err)
	}
	u := uint32(ui64)
	return u
}

func StringsToParents(s []string) inputs.Parents {
	var p inputs.Parents
	for _, v := range s {
		p = append(p, inputs.EventId(v))
	}
	return p

}
