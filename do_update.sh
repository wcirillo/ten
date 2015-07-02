echo "Running $0 at `date`"
hg fetch && hg summary && hg push
