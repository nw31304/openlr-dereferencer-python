from webtool import WebToolMapReader, Line
from time import perf_counter_ns

rdr = WebToolMapReader(host="",dbname="openlr",schema="texas",lines_table="roads",nodes_table="intersections")

start = perf_counter_ns()
for _ in range(0,100):
    res=rdr.match("C7yP6xTT6QEWE/t6/+0BCA==")
end = perf_counter_ns()
print(end-start)
