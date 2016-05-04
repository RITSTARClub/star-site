'use strict';
window.addEventListener('load', function () {
	var semesterPicker = document.getElementById('semesterPicker');
	if (semesterPicker) {
		semesterPicker.semester.onchange = function (e) {
			window.open('?semester=' + e.target.value, '_self');
		}
	}
}, false);
