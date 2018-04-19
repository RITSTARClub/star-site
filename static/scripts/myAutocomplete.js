var input;
var hidden_input;
var awesomplete;
var current_members;

/**
 * The ready function loads in the awesomplete functionality from awesomplete.js
 * Also preps the autocomplete functionality and can take multiple inputs
 */
$(document).ready((function() {
	input = document.getElementsByClassName("awesomplete").item(1);
	input.value = input.value.substring(0,input.value.length-1); //removes the last comma from the input value
	hidden_input = document.getElementById("runners_id");
	awesomplete = new Awesomplete(input,{
		filter: function(text, input) {
		  return Awesomplete.FILTER_CONTAINS(text, input.match(/[^,]*$/)[0]);
		},
		replace: function(text) {
			//places the name into the visible one
		  var before = this.input.value.match(/^.+,\s*|/)[0];
		  this.input.value = before + text + ", ";
		  //adds the id number to the actual input
		  addHiddenMemberID(text);
		}
	});
	getMembers();
}));

/**
 * Queries the data for members that match what is types. The query given is either everything inside of the input or the last string past the last comma.
 */
function getMembers(){
	var query;
	if(input.value.includes(",")){
		var tempArray = input.value.split(",");
		query = tempArray[tempArray.length - 1].replace(/\s/g, '');
	}else{
		query = input.value;
	}

	if(query.length >= 2){
		$.ajax({
		  type: "GET",
		  url: "/missions/search/",
		  data: { search_query: query}
		}).done(function( data ) {
			awesomplete.list = JSON.parse(data);
			current_members = JSON.parse(data);
		});
	}
	input.focus();
}

/**
 * Removal functionality so that both the visible and hidden inputs are in sync.
 * Removes the values that are split by the commas. Also removes the free flowing comma in the hidden input if applicable.
 */
function removeMembers(){
	var seenValArray = input.value.split(",");
	var hiddenValArray = hidden_input.value.split(",");
	var seenLength = seenValArray.length;
	var hiddenLength = hidden_input.value.length;

	if(seenLength !== hiddenValArray.length){
		var remove = hiddenValArray.pop();
		hidden_input.value = hidden_input.value.replace(remove,"");
		if(hidden_input.value[hiddenLength -1] === ","){
			hidden_input.value = hidden_input.value.substr(0,hiddenLength - 1);
		}
	}
}

/**
 * Adds member if to the hidden input.
 * @param textLabel
 */
function addHiddenMemberID(textLabel){
	current_members.forEach(function(member){
		//console.log("mLabel",member.label);
		if(textLabel.label === member.label){
			if(hidden_input.value.length > 0 ){
				hidden_input.value = hidden_input.value + "," + member.value;
			}else{
				hidden_input.value = member.value;
			}
		}
	});
}