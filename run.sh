#!/bin/bash

nhosts=2
nflows=1
cases=( "minTCP" "TCP" )
workloads=( "websearch" "datamining" )

# Run on web search workload
for w in "${workloads[@]}"
do
  for i in "${cases[@]}"
    do
      sudo python pfabric.py --outputdir output_"$w" --tcp "$i" --workload workloads/"$w"_scaled6.txt --nflows-per-host "$nflows" --nhosts "$nhosts"
    done

    # Plot
    sudo python plot_results.py --dir output_"$w" --out output_$w/"$w".png
done

#sudo shutdown -h now