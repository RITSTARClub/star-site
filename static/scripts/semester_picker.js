'use strict';
window.addEventListener('load', function () {
	var semesterPicker = document.getElementById('semesterPicker');
	if (semesterPicker) {
		semesterPicker.semester.onchange = function (e) {
			if (location.href.match('/members')) {
				window.open('?q=semester:' + e.target.value, '_self');
			} else {
				window.open('?semester=' + e.target.value, '_self');
			}
		}
	}
}, false);
