* go through the code and find anything that needs to be fixed 
* write unit tests (write a unit test to verify docs are in line with code)
* run lint/pep8 checks 
* Continue to look for a HTTP parsing library so I don't have to parse all this myself. 
* Add a "add_child" method that will add a child to the correct parent and instantiate any intermediate objects needed. e.g.: hc.add_child(request) on an empty container should create a log, create a new entry, and add the request to that entry. 
* write har validator

* figure out a way to figure out if anything from a URL ends up in any requets or responses down the line....