# Agent Skills

This is a collection of the stuff I've put together to make my own work...faster?  We'll see about that.

## Made by me (and copilot, ofc)

### repo-index

makes a metadata file of all your checked-out repos

#### Overview

* expects you to have an env var `$AGENTS_REPOS_ROOT` pointing to the parent folder where you keep your code repos
  * if you don't have that, it stops and tells you to make it and restart your terminal
* finds all folders in that root that has a `.git` folder
* asks you if you want to ignore any of them
* creates a metadata file `repos.json` of all your git repos with
  * project name
  * file path (using the env-var so the skill stays re-usable)
  * tech stack: unknown, or one or more of: Angular, Node.js, Go, Java (Maven), Python, Docker, Terraform, Kustomize, Helm, Rust, Ruby, Elixer (is not exhaustive cuz I trained it on the junk I had checked out)
 
#### Why? 

To save subsequent skills from having to look in every single folder for relevant stuff.  Useful if you're doing, say, "Update all my terraform projects to the latest version of terraform".  Instead of asking for a bunch of folder permissions and hunting every folder for *.tf, etc, this should help other skills/agents limit their search scope to only the repos in the metadata list that have "terraform" in their tech stack.

## Made by others, modified by me

### skills-creator

This is my modification of Anthropic's [skills-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator).  

#### Changes I have made so far

* removed references to their [legacy backwards compatibility code ](https://github.com/anthropics/skills/blob/main/skills/skill-creator/scripts/aggregate_benchmark.py#L27)
  * also removed any reference to `runs-#` because it no longer does multiple runs of an eval in an iteration for the benchmark and agents weren't putting things in the file structure the python script expected, so then they'd get confused why the python script broke, had to go look at the code, fix their directory...etc.  wasted time and credits.
* removed all versions of the word "assertion" in favor of "expectation"...
  * because humans(?) were using it interchangeably with "expectation", but "assertion" was used more, and in the actual variable/structure's in the scripts, again causing agents to call things one or the other and break the scripts
* changed text in the SKILL to encourage evaluations to be in clean-room environments, not operate on real-world files
  * when writing evals, if the evals need to read files or folders, create those in an `evals/fixtures` folder
  * consider the `evals/fixtures` folder immutable: only read from it, don't edit those files
  * when running an eval, copy the files you need from the `evals/fixtures` folder into `interation-N/eval-N/` so that each eval has their own personal test space
  * if you need to write outputs as an eval, only put them in `iteration-N/eval-N/outputs` so that the tests are repeatable, don't overwrite each others' files, and we can run the grader/benchmark stuff each independently
* put a skill's `workspace` folder into the skill's folder, not a sibling because that's annoying to me, personally
  * to that end, add `workspace/` to the root level `.gitignore` file if it isn't there already so we don't check any workspace files in
 
#### Modifications I'd like to make in the future

* have skills-creator prefer and interview/test-first approach to writing skills

