package main

import (
	"Lachesis/common"
	"Lachesis/inputs"
	"Lachesis/lachesis"
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
)

// About the input file network: Node Sequence; []Node connections; []Events owned by the node
// About the input file events: the first line is the node; Event ID; Epoch; Sequence; Frame; Creator; []Parents

func main() {
	//Nodes in the network
	node := make(inputs.Network)
	// input network file
	f1, err := os.Open("./inputs/network.txt")
	if err != nil {
		fmt.Println("Network file input error!", err)
		panic(err)
	}
	// reader
	r := bufio.NewReader(f1)
	for {
		line, err := r.ReadString('\n')
		line = strings.TrimSpace(line)
		if err != nil && err != io.EOF {
			fmt.Println("Read network file error!", err)
			panic(err)
		}
		if err == io.EOF {
			break
		}
		//fmt.Println(line)
		strNode := strings.Split(line, ";")
		strConn := strings.Split(strNode[1], ",")
		strHash := strings.Split(strNode[2], ",")
		var nodeProperty inputs.Node
		nodeProperty.SetConnections(strConn)
		nodeProperty.SetDag(strHash)
		node[strNode[0]] = nodeProperty
	}

	// Events owned by one node
	events := make(inputs.Events)
	// input events file
	f2, err := os.Open("./inputs/IsFork_test.txt")
	if err != nil {
		fmt.Println("Events file input error!", err)
		panic(err)
	}
	// reader
	r = bufio.NewReader(f2)
	i := 0
	var n string
	for {
		line, err := r.ReadString('\n')
		line = strings.TrimSpace(line)
		if err != nil && err != io.EOF {
			fmt.Println("Read events file error!", err)
			panic(err)
		}
		if err == io.EOF {
			break
		}
		//fmt.Println(line)
		if i == 0 {
			n = line
		} else {
			var event inputs.Event
			StrEvent := strings.Split(line, ";")
			event.SetNode(n)
			event.SetId(StrEvent[0])
			event.SetEpoch(common.StringToUint32(StrEvent[1]))
			event.SetSeq(common.StringToUint32(StrEvent[2]))
			event.SetFrame(common.StringToUint32(StrEvent[3]))
			event.SetCreator(StrEvent[4])
			event.SetParents(strings.Split(StrEvent[5], ","))
			event.SetHighestEventsVector(events)
			events[StrEvent[0]] = event
			fmt.Println(event)
		}
		i++
	}
	//fmt.Println(events)

	validators := make(lachesis.Validators)
	var v1 lachesis.Validator
	v1.SetWeight(1)
	validators["a"] = v1

	var v2 lachesis.Validator
	v2.SetWeight(2)
	validators["b"] = v2

	var v3 lachesis.Validator
	v3.SetWeight(2)
	validators["c"] = v3

	var v4 lachesis.Validator
	v4.SetWeight(1)
	validators["d"] = v4

	var A string = "EventA04"
	var B string = "EventA01"
	if lachesis.ForklessCause(A, B, events, validators) {
		fmt.Println(A, "is forkless caused by", B)
	} else {
		fmt.Println(A, "is not forkless caused by", B)
	}

}
