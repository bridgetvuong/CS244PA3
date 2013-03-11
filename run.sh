#!/bin/bash

nhosts=20
timeperload=360
cases=( "minTCP" "TCP" )
workloads=( "websearch_scaled3" "datamining_scaled3" )

# Run on web search workload
for w in "${workloads[@]}"
do
  for i in "${cases[@]}"
    do
      sudo python pfabric.py --outputdir output_"$w" --tcp "$i" --workload workloads/"$w".txt --time "$timeperload" --nhosts "$nhosts"
    done

    # Plot
    sudo python plot_results.py --dir output_"$w" --out output_"$w"/"$w".png
done

#sudo shutdown -h now