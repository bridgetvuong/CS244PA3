#!/bin/bash

nhosts=20
runtime=1200
cases=( "minTCP" "TCP" )
workloads=( "websearch_scaled3" "datamining_scaled3")

# Run on web search workload
for w in "${workloads[@]}"
do
  for i in "${cases[@]}"
    do
      sudo python ./pfabric.py --outputdir "$w"_"$nhosts"h_"$runtime"s --tcp "$i" --workload workloads/"$w".txt --time "$runtime" --nhosts "$nhosts"
    done

    # Plot
    sudo python ./plot_results.py --dir "$w"_"$nhosts"h_"$runtime"s --out "$w"_"$nhosts"h_"$runtime"s/"$w"_"$nhosts"h_"$runtime"s.png
done

#sudo shutdown -h now
