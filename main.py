import re, os, requests, time, base64
from github import Github, Auth

auth = Auth.Token(input("Github token (e.g. ghp_***********): "))
github = Github(auth=auth)

session = requests.Session()
session.headers.setdefault("Authorization", f"Bearer {auth.token}")

def sizeof_fmt(num):
    for unit in ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}"
        num /= 1024.0
    return f"{num:.1f}YB"


authorUser = None
while authorUser == None:
    try:
        authorUser = github.search_users(input("Github repo author's name: ")).get_page(0)[0]
        break
    except IndexError:
        print("[!] Couldn't find author with given name.")
print("Found author:", authorUser.login)

repo = authorUser.get_repo(input(f"{authorUser.login}'s github repo name: "))
while repo == None:
    try:
        repo = authorUser.get_repo(input(f"{authorUser.login}'s github repo name: "))
        break
    except:
        print(f"[!] Couldn't find github repo with given name from {authorUser.login}.")
print("Found repo:", repo.name)

foldersExclude = input("Folders names which you would like to exclude (e.g. bin, out): ").split(", ")
filesExclude = input("Files names which you would like to exclude (e.g. coolfile.cs, anotherfile.cs): ").split(", ")
extensionsExclude = input("File with extensions you would like to exclude (e.g. cs, cpp, c, py): ").split(", ")

foldersExclude_re = None
if foldersExclude[0] != '':
    foldersExclude_re = re.compile('|'.join([re.escape(folder.strip()) for folder in foldersExclude]), re.IGNORECASE)

extensionsExclude_re = None
if extensionsExclude[0] != '':
    extensionsExclude_re = re.compile(r'\.(' + '|'.join([re.escape(ext.strip()) for ext in extensionsExclude]) + r')$', re.IGNORECASE)

def find_tree(tree_url):
    return session.get(tree_url).json()["tree"]

def check_tree(tree: list[dict], custom_path = str | None):
    if custom_path == None:
        custom_path = ""
    for tree_content in tree:
        if tree_content["type"] == "tree":
            if (foldersExclude[0] != '' and tree_content["path"] in foldersExclude):
                print("Excluded by folder name:", tree_content["path"])
            else:
                new_path = custom_path + "/"  + tree_content["path"]
                os.mkdir(GITHUB_REPO_NAME+new_path)
                check_tree(find_tree(tree_content["url"]), new_path)
        else:
            new_path = custom_path + "/" + tree_content["path"]
            if (filesExclude[0] != '' and tree_content["path"] in filesExclude) or (extensionsExclude_re != None and extensionsExclude_re.search(tree_content["path"])):
                print("Excluded by file name or extension:", tree_content["path"])
            else:
                print(f"Downloading {tree_content["path"]} ({sizeof_fmt(tree_content["size"])})")
                response = session.get(tree_content["url"])
                while True:
                    if response.status_code == 200:
                        open(GITHUB_REPO_NAME+new_path, 'wb+').write(base64.b64decode(response.json()["content"]))
                        print(f"File saved.")
                        break
                    elif response.status_code == 404:
                        print(f"Couldn't find file.")
                        break
                    else:
                        print(f"Rate limit! Waiting 10 seconds and then trying again.. {response.status_code}")
                        time.sleep(10)


tree = input("Tree name: ")
GITHUB_REPO_NAME = f"{authorUser.login}-"
if tree != '':
    GITHUB_REPO_NAME += f"{tree}/"
else:
    GITHUB_REPO_NAME += f"{repo.name}/"

if not os.path.isdir(GITHUB_REPO_NAME):
    os.mkdir(GITHUB_REPO_NAME)

if tree != '':
    # try:
        check_tree(repo.get_git_tree(tree).raw_data["tree"], None)
    # except:
    #     input(f"[!] Couldn't find github repo with given tree name.")
    #     exit(-1)

else:
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop()
        if file_content.type == "dir":
            if (foldersExclude_re != None and foldersExclude_re.search(file_content.path)):
                print("Excluded by folder name:", file_content.path)
            else:
                print(file_content.path)
                os.mkdir(GITHUB_REPO_NAME+file_content.path)
                contents.extend(repo.get_contents(file_content.path))
        else:
            if (filesExclude[0] != '' and file_content.name in filesExclude) or (extensionsExclude_re != None and extensionsExclude_re.search(file_content.name)):
                print("Excluded by file name or extension:", file_content.path)
            else:
                print(f"Downloading {file_content.name} ({sizeof_fmt(file_content.size)})")
                response = session.get(file_content.download_url)
                while True:
                    if response.status_code == 200:
                        open(GITHUB_REPO_NAME+file_content.path, 'wb+').write(response.content)
                        print(f"File saved.")
                        break
                    elif response.status_code == 404:
                        print(f"Couldn't find file.")
                        break
                    else:
                        print(f"Rate limit! Waiting 10 seconds and then waiting again..")
                        time.sleep(10)

print("Cloning complete!")