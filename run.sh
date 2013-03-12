#!/bin/bash

nhosts=20
runtime=300
cases=( "minTCP" "TCP" )
workloads=( "websearch_scaled3" "datamining_scaled3" )
scale=3

# Run on web search workload
for w in "${workloads[@]}"
do
  for i in "${cases[@]}"
    do
      sudo python ./pfabric.py --outputdir "$w"_"$nhosts"h_"$runtime"s --tcp "$i" --workload workloads/"$w".txt --time "$runtime" --nhosts "$nhosts"
    done

    # Plot
    sudo python ./plot_results.py --dir "$w"_"$nhosts"h_"$runtime"s --scale $scale
done

#sudo shutdown -h now
