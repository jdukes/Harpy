* create a "header" and "cookie" object with "render" and "devour" methods
* write a burp interface
** should __repr__ and __iter__ as a list, in order based on the __seq__ field
** should have __contains__ that checks header names
*** e.g.: "Content-Length" in headers
** should be possible to access as a dictionary
** should have "add" "set" (add or update) and "delete" methods to add, update, or delete keys
*** parent should have a way to use "replace" on headers and cookies
* go through the code and find anything that needs to be fixed 
* write unit tests (write a unit test to verify docs are in line with code)
* run lint/pep8 checks 
* Continue to look for a HTTP parsing library so I don't have to parse all this myself. 
* Add a "add_child" method that will add a child to the correct parent and instantiate any intermediate objects needed. e.g.: hc.add_child(request) on an empty container should create a log, create a new entry, and add the request to that entry. 
* write har validator

