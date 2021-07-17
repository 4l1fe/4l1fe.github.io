select grp,
       count(*),
       min(value1) as min1,
       max(value1) as max1,
       avg(value1) as avg1,
       sum(value1) as sum1,
       min(value2) as min2,
       max(value2) as max2,
       avg(value2) as avg2,
       sum(value2) as sum2,
       min(value3) as min3,
       max(value3) as max3,
       avg(value3) as avg3,
       sum(value3) as sum3
from random_data
group by grp;