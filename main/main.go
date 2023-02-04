package main

import (
	"Lachesis/common"
	"Lachesis/dag"
	"Lachesis/idx"
	"Lachesis/lachesis"
	"Lachesis/pos"
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
)

// About the input file network: Node Sequence; []Node connections; []Events owned by the node
// About the input file events: the first line is the node; Event ID; Epoch; Sequence; Creator; []Parents

func main() {
	// Set the validators
	var validators pos.Validators
	validators.NewValidator("a", 1)
	validators.NewValidator("b", 1)
	validators.NewValidator("c", 1)
	validators.NewValidator("d", 1)

	// Storage
	var store lachesis.Store
	store.StoreValidators(validators)

	// Nodes in the network
	node := make(dag.Network)
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
		var nodeProperty dag.Node
		nodeProperty.SetConnections(strConn)
		nodeProperty.SetDag(strHash)
		node[strNode[0]] = nodeProperty
	}

	// Events owned by one node
	events := make(dag.Events)
	// input events file
	f2, err := os.Open("./inputs/forklessCause_test.txt")
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
			var event dag.Event
			StrEvent := strings.Split(line, ";")
			event.SetNode(idx.NodeId(n))
			event.SetId(idx.EventId(StrEvent[0]))
			event.SetEpoch(idx.Epoch(common.StringToUint32(StrEvent[1])))
			event.SetSeq(idx.Seq(common.StringToUint32(StrEvent[2])))
			event.SetCreator(idx.ValidatorId(StrEvent[3]))
			event.SetParents(common.StringsToParents(strings.Split(StrEvent[4], ",")))
			event.SetEvent(&events)
			event.SetFrame(store.CalcFrameIdx(event))
			events[idx.EventId(StrEvent[0])] = event
			store.StoreEvents(events)
		}
		i++
	}

	for id, _ := range events {
		fmt.Println(events[id])
	}

	var A idx.EventId = "EventA04"
	var B idx.EventId = "EventB01"
	if lachesis.ForklessCause(events[A], events[B], store) {
		fmt.Println(A, "is forkless caused by", B)
	} else {
		fmt.Println(A, "is not forkless caused by", B)
	}

	//for k, v := range store.Frames() {
	//	fmt.Println("------------------------Frame", k)
	//	for _, j := range v {
	//		fmt.Print(j.Id())
	//	}
	//}

}
