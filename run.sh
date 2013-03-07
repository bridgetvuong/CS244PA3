websearch = "workloads/websearch.txt"
datamining = "workloads/datamining.txt"
nflows = 100
nhosts = 54
cases = ("minTCP" "TCP")

# Run on web search workload
for i in "${cases[@]}"
do
sudo python pfabric.py --outputdir output_websearch --tcp $i --workload $websearch --nflows $nflows --nhosts $nhosts
done

# Run on data mining workload
for i in "${cases[@]}"
do
sudo python pfabric.py --outputdir output_datamining --tcp $i --workload $datamining --nflows $nflows --nhosts $nhosts
done

# Plot