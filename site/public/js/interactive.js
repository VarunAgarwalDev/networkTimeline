function getData(currType){
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

  var postman = $.post("https://archerbitcointimeline.herokuapp.com/"+currType,
    {
        addresses: address,
        start:startDate,
        end:endDate
    });
  postman.success(function(data, status){
        alert(data);
  });
}

//Converts JSON into a CSV
function convertJSONToCSV(args) {
    var result, ctr, keys, columnDelimiter, lineDelimiter, data;

    data = args.data || null;
    if (data == null || !data.length) {
        return null;
    }

    columnDelimiter = args.columnDelimiter || ',';
    lineDelimiter = args.lineDelimiter || '\n';

    keys = Object.keys(data[0]);

    result = '';
    result += keys.join(columnDelimiter);
    result += lineDelimiter;

    data.forEach(function(item) {
        ctr = 0;
        keys.forEach(function(key) {
            if (ctr > 0) result += columnDelimiter;

            result += item[key];
            ctr++;
        });
        result += lineDelimiter;
    });

    return result;
}

function downloadCSV(args) {
    var data, filename, link, curr;
    var csv = convertJSONToCSV({
        data: getData(args.curr)
    });
    if (csv == null) return;

    filename = args.filename || 'exportTransactions.csv';

    if (!csv.match(/^data:text\/csv/i)) {
        csv = 'data:text/csv;charset=utf-8,' + csv;
    }
    data = encodeURI(csv);

    link = document.createElement('a');
    link.setAttribute('href', data);
    link.setAttribute('download', filename);
    link.click();
}
