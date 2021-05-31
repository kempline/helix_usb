import xlrd


book = xlrd.open_workbook("./doc/Module_IDs.xls")

print("The number of worksheets is {0}".format(book.nsheets))
print("Worksheet name(s): {0}".format(book.sheet_names()))

for i in range(0, book.nsheets):
    sh = book.sheet_by_index(i)
    # print("{0} {1} {2}".format(sh.name, sh.nrows, sh.ncols))
    # print("Cell D30 is {0}".format(sh.cell_value(rowx=29, colx=3)))
    for rx in range(1, sh.nrows):
        if sh.row(rx)[2].value != '':
            module_id = sh.row(rx)[2].value
            try:
                module_id = int(module_id)
                module_id = str(module_id)
            except ValueError:
                pass

            if module_id.startswith("'"):
                module_id = module_id[1:]
            if module_id == 'n/a':
                pass
            else:
                print("'" + module_id + "':\t['" + sh.row(rx)[1].value + "', '" + sh.row(rx)[0].value + " (mono)'],")
        if sh.row(rx)[3].value != '':
            module_id = sh.row(rx)[3].value
            try:
                module_id = int(module_id)
                module_id = str(module_id)
                if len(module_id) == 1:
                    module_id = '0' + module_id
            except ValueError:
                pass

            if module_id.startswith("'"):
                module_id = module_id[1:]
            if module_id == 'n/a':
                pass
            else:
                print("'" + module_id + "':\t['" + sh.row(rx)[1].value + "', '" + sh.row(rx)[0].value + " (stereo)'],")
        if sh.row(rx)[4].value != '':
            module_id = sh.row(rx)[4].value
            try:
                module_id = int(module_id)
                module_id = str(module_id)
            except ValueError:
                pass
            if module_id.startswith("'"):
                module_id = module_id[1:]
            if module_id == 'n/a':
                pass
            else:
                print("'" + module_id + "':\t['" + sh.row(rx)[1].value + "', '" + sh.row(rx)[0].value + " (legacy)'],")
