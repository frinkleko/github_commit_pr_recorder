# github_commit_pr_recorder
Crawl commits and prs into csv, given user name and time frame. And I know there are **lots of** simliar codes to do the same function!

Then do your analysis, for example, how many repos, commits and toward how many organizations.

## Requirements
bs4, pandas, requests

## Usage

Modify parameters for `main` function.
```python
    main(
        github_username=github_username,
        output_file=output_file,
        start_time=None,
        end_time=None,
        github_token=None,
    )
```
and run 
```bash
python main.py
```
