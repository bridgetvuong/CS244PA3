nflows = 100
nhosts = 54
cases = ("minTCP" "TCP")
workloads = ("websearch" "datamining")

websearchdir = "output_websearch"

# Run on web search workload
for w in "${workloads[@]}"
do
    for i in "${cases[@]}"
    do
	sudo python pfabric.py --outputdir output_$w --tcp $i --workload workloads/$w.txt --nflows-per-host $nflows --nhosts $nhosts
    done

    # Plot
    sudo python plot_results.py --dir output_$w --out output_$w/$w.png
done