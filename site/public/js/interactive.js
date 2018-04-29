function getData(currType){
  var finalJson;
  if(currType == "btc"){
    formResp = document.getElementById("search_form_btc");
  }else{
    formResp = document.getElementById("search_form_nem");
  }

  if(formResp.length == 3){
    address = formResp.elements[0].value;
    startDate = formResp.elements[1].value;
    endDate = formResp.elements[2].value;
  }else {
    alert("Please enter all values");
  }

  $("#dvLoading").show();
  var postman = $.post("https://archerbitcointimeline.herokuapp.com/"+currType,
    {
        addresses: address,
        start:startDate,
        end:endDate
    });
  postman.success(function(data, status){
      //Hide loading screen
        $("#dvLoading").hide();
        console.log(data);
        //return json to be converted to CSV
        finalJson = data;
  });
  return finalJson;
}

//Converts JSON into a CSV
function convertJSONToCSV(objArray) {
  var array = typeof objArray != 'object' ? JSON.parse(objArray) : objArray;
            var str = 'Sending Address, Receiving ID, Receiving Address, Value, Source ID, Transaction ID' + '\r\n';

            for (var i = 0; i < array.length; i++) {
                var line = '';
                for (index in array[i]) {
                    if (line != '') line += ','
                    line += array[i][index];
                    console.log(array[i][index]);
                }

                str += line + '\r\n';
            }
            return str;
}

function downloadCSV(args) {
    var data, filename, link, curr;
    //For some reason this is returning undefined:
    //It should return a json in the d3 format of nodes and links
    msgg = getData(args.curr);
    console.log(typeof(msgg));

    //From here onwards everything else is working
    var csv = convertJSONToCSV(msgg["links"]);
    if (csv == null){
      console.log("csv is returned null");
      return;
    }

    filename = args.filename || 'exportTransactions.csv';

    //console.log(csv);
    if (!csv.match(/^data:text\/csv/i)) {
        csv = 'data:text/csv;charset=utf-8,' + csv;
    }
    data = encodeURI(csv);

    link = document.createElement('a');
    link.setAttribute('href', data);
    link.setAttribute('download', filename);
    link.click();
}
