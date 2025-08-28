import pygsheets

gc = pygsheets.authorize(service_file="service_account.json")
sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1U4NNhjlMdfN0rhgANzsroBCvBJgtCX3rr8_RKQt06KQ/edit?gid=0#gid=0")
wks = sh.sheet1
print(wks.get_all_records())
wks.update_row(1, ["Clause ID", "Contract Clause", "Regulation", "Risk Level", "AI Analysis"])
print("Pyg sheets connected.")
