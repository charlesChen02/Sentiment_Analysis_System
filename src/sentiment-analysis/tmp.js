
// <!-- transparent function for reducing to total number of tweets collected -->
function(keys,values,rereduce) {
    result = {'sum' : 0,'count': 0};
        if (rereduce) {
            for (var i = 0; i < values.length; i++) {
                result.sum += values[i].sum;
                result.count += values[i].count;
            }
            return results;
        } else {
            for (var j = 0; j < values.length; j++) {
                results.sum += values[j].sum;
            }
            results.count = values.length;
            return results.sum;
        }
}

// <!-- map function for each city -->
function(doc) {
    emit([doc.id,doc.place.location],doc.polarity);
}
// reduce function for city specific polarity count
function(keys,values,rereduce) {
    var cities = [];
    var score = 0;
    if (!rereduce) {
        keys.forEach(function (key) {
            var city = key[1];
            // if the city not in dict
            if (cities.indexOf(city) < 0) {
                cities.push(city);
            }
            score += values;
            
        });
    }
    return {cities : cities, scores : score};
} 
// not sure if this works.
