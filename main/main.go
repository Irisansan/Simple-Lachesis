package main

import (
	"Lachesis/common"
	"Lachesis/inputs"
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
	var Events [10]inputs.Event
	// input events file
	f2, err := os.Open("./inputs/events.txt")
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
			Events[i].SetNode(n)
			StrEvent := strings.Split(line, ";")
			Events[i].SetId(StrEvent[0])
			Events[i].SetEpoch(common.StringToUint32(StrEvent[1]))
			Events[i].SetSeq(common.StringToUint32(StrEvent[2]))
			Events[i].SetFrame(common.StringToUint32(StrEvent[3]))
			Events[i].SetCreator(common.StringToUint32(StrEvent[4]))
			Events[i].SetParents(strings.Split(StrEvent[5], ","))
		}
		i++
	}
	//fmt.Println(node)
	fmt.Println(Events)
}
