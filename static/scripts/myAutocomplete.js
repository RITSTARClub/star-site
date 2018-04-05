var input;
						var hidden_input;
						var awesomplete;
						var current_members;
						$(document).ready((function() {
						    input = document.getElementsByClassName("awesomplete").item(1);
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

						function getMembers(){
						    var query;
						    if(input.value.includes(",")){
						        var tempArray = input.value.split(",");
                                query = tempArray[tempArray.length - 1].replace(/\s/g, '');
                            }else{
						        query = input.value;
                            }
						    if(input.value.length >= 2){
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