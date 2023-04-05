## Generating inputs

-  run `python3 graph.py`

## Script inputs:

If you press enter, the defaults take hold, otherwise the inputs are "y"/"n", an int value for how many graphs, 
levels, nodes(validators) you would prefer, and a float value of 0-1.0 for the probability of a random validator 
being a cheater, a node/validator being present at a given time step, and a node/validator having an edge to a
parent in the prior time step.

-  Annotate graphs (y/n): (Default is no) 
-  How many graphs would you like to generate: (Default is 50) 
-  Enter the probability that a random validator node is a cheater: (Default is 0.2) 
-  Enter the number of levels in each graph or type 'r' or 'random' for a random value each iteration: (Default is 10)
-  Enter the number of nodes in each level or type 'r' or 'random' for a random value each iteration: (Default is 5) 
-  Enter the probability that a node is present or type 'r' or 'random' for a random value each iteration: (Default is 0.65) 
-  Enter the probability that a node observes another validator or type 'r' or 'random' for a random value each iteration: (Default is 0.3) 

## Script outputs:

-  `graph_{i}.pdf` file is created in /graphs/ as a pictorial representation of the DAG
-  `graph_{i}.txt` file is created in /graphs/ as the first textual representation of the DAG
-  `events_{i}.txt` file is created in /graphs/ as the second textual representation of the DAG
