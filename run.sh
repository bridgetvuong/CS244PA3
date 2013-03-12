#!/bin/bash

nhosts=20
workloads=( "websearch" "datamining" )
runtimes=( 180 300 )
cases=( "minTCP" "TCP" )
scale=1


# Run on web search workload
for (( i=0; i<${#workloads[@]}; i++ ))
do
  sudo rm -rf "${workloads[$i]}"_"$nhosts"h_"runtime"s

  w="${workloads[$i]}"
  t="${runtimes[$i]}"

  for c in "${cases[@]}"
    do
      sudo python ./pfabric.py --outputdir "$w"_"$nhosts"h_"$t"s --tcp "$c" --workload workloads/"$w".txt --time "$t" --nhosts "$nhosts"
    done

    # Plot
    sudo python ./plot_results.py --dir "$w"_"$nhosts"h_"$t"s --scale "$scale"
done

#sudo shutdown -h now
