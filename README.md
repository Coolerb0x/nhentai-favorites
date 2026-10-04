# nhentai-favorites

Export your nhentai favorites to a csv file using the official [nhentai API](https://nhentai.net/api/v2/docs).

## how to use?

`pip install -r ".\requirements.txt"`
run `nfavorites.py` once, it will exit and generate `set.yaml`
generate an API key in your [account settings](https://nhentai.net/user/settings#apikeys)
when asked "We're curious — what are you building?", you can paste:

```text
Using https://github.com/phillychi3/nhentai-favorites to export my favorites.
```

open `set.yaml` and enter your API key:

```yaml
apikey: YOUR_API_KEY
```

run `nfavorites.py` again and it will generate `output.csv`

![alt text](https://github.com/phillychi3/nhentai-favorites/blob/main/image/csv.png?raw=true)
