Next steps:

Variables declared inside of exec statements aren't allowed - something about how the symtables are getting merged doesn't work
Look at `vm.exec_source()`