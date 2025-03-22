
/*
// The DataTable library is a jQuery/JavaScript Library 
// that allows formatting and add functionality (sort, search, paging etc.)
// to any "well-formatted" html Table. 
// It requires jQuery 1.8 to provide its functionality.
// More on DataTables here: https://datatables.net/

// The MakeDataTable function below uses the DataTables library
// The library is loaded, along with jQuery, in base.html and available everywhere.
// Function takes the div containing the Table. 
// Calls the DataTable library to create a "DataTable".

*/

function ClearActive() {
    $('.nav-link').removeClass('active selectedTab');
}

function MakeDataTable(tableDivId)
{
	const TableDiv = '#' + tableDivId;

	$(TableDiv).DataTable({
		order: [0, 'asc'],
		responsive: true,

		//paging: false,
		paging: true,
		pageLength:20,
		searching: true,

		language: {

			"search": "Filter results:",
			"zeroRecords": "No records found",
		},
	});
}
	
