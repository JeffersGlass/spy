###

    def inner_main(args):

    modname = args.filename.stem
    importer = ImportAnalyzer(vm, modname)
    importer.parse_all()
    importer.import_all()
    w_mod = vm.modules_w[modname]

    if args.execute and not args.redshift:
        execute_spy_main(args, vm, w_mod)
        return

    if (args.redshift or args.colorize) and args.execute:
        execute_spy_main(args, vm, w_mod)
        return

    backend = CBackend(vm, modname, config, build_dir, dump_c=dump_c)
    backend.cwrite()
    backend.write_build_script()
    outfile = backend.build()

    print(f"[{config.build_type}] {executable} ")

def execute_spy_main(args: Arguments, vm: SPyVM, w_mod: W_Module) -> None:
    w_main = w_mod.getattr_maybe("main")
    if args.redshift: w_main = w_main.w_redshifted_into
    w_res = vm.fast_call(w_main, [])

###


        if '_list.spy' not in mod.filename:
            imports = [d for d in mod.decls if isinstance(d, spy.ast.Import)]
            need_to_import_list = not any((i.ref.attr == "List" and i.ref.modname == "_list") for i in imports)


            for node in mod.walk():
                if isinstance(node, spy.ast.List):
                    print("Found a List node in the AST")
                    # There is a List node in the AST
                    if need_to_import_list:
                        print("Importing _list.List")
                        import_list()
                        need_to_import_list = False

                    """ value=Call(
                        func=GetItem(
                            value=Name(id='List'),
                            args=[
                                Name(id='i32'),
                            ],
                        ),
                        args=[],
                    ), """
                    
                    new_node = spy.ast.Call(
                        loc=node.loc,
                        func = spy.ast.GetItem(
                            loc=Loc.fake(),
                            value = spy.ast.Name(loc=Loc.fake(), id='List'),
                            args = spy.ast.Name(loc=Loc.fake(), id='i32'),
                        ),
                        args = node.items
                    ) 
                    node = new_node
                    print(node)
            
        mod.pp()


-------


def import_builtin_List(self, l: spy.ast.List, mod) -> None:
        print("Stepped into import_builtin_List")
        if '_list.spy' not in mod.filename:
            imports = [d for d in mod.decls if isinstance(d, spy.ast.Import)]
            if any((i.ref.attr == "List" and i.ref.modname == "_list") for i in imports): 
                print("No need to import again")
                return # _list.List already imported
        print("Importing _list.List")

        ref = spy.ast.ImportRef(
            modname = "_list",
            attr = "List"
        )
        list_imp = spy.ast.Import(
            loc = Loc.fake(),
            loc_asname = Loc.fake(),
            ref = ref,
            asname = "List"
        )
        mod.decls.append(list_imp)
        
        l = None