# GHAS activation and coverage optimization 

------------------------------------------------------------
# Current coverage

Total active committers: 2
Total repositories with GHAS: 1
Total repositories without GHAS: 46
Coverage: 2.13%
----------------------------------------
# Increase coverage with currently consumed licenses 

**Turning GHAS on following repositories will not consume additional licenses**
- Repositories with active committers already consume GHAS license:
	 -  Repository: empty-one | GHAS Status: False | Last Pushed At: 2023-10-25T12:47:33Z | Active Committers: ['theztefan']
- Repositories without active committers:
	 -  Repository: ado-project-migration | GHAS Status: False | Last Pushed At: 2022-05-12T10:54:04Z | Active Committers: []
	 -  Repository: new-secret-demo | GHAS Status: False | Last Pushed At: 2023-02-24T16:31:40Z | Active Committers: []
	 -  Repository: dependancy-compare | GHAS Status: False | Last Pushed At: 2023-07-24T13:37:04Z | Active Committers: []
	 -  Repository: octo-gallery | GHAS Status: False | Last Pushed At: 2023-07-25T18:43:20Z | Active Committers: []
	 -  Repository: gradle-dependancy-test | GHAS Status: False | Last Pushed At: 2023-09-06T15:09:18Z | Active Committers: []
	 -  Repository: elc-demo | GHAS Status: False | Last Pushed At: 2023-07-09T03:04:58Z | Active Committers: []
	 -  Repository: hm-demo | GHAS Status: False | Last Pushed At: 2023-10-17T21:37:47Z | Active Committers: []
	 -  Repository: new-test-repo | GHAS Status: False | Last Pushed At: 2022-12-16T13:23:15Z | Active Committers: []
	 -  Repository: goserver | GHAS Status: False | Last Pushed At: 2023-01-09T16:36:30Z | Active Committers: []
	 -  Repository: autodep | GHAS Status: False | Last Pushed At: 2023-01-12T14:17:21Z | Active Committers: []
	 -  Repository: autodep-priv | GHAS Status: False | Last Pushed At: 2023-01-12T14:17:41Z | Active Committers: []
	 -  Repository: exercise-enable-code-scanning-using-codeql | GHAS Status: False | Last Pushed At: 2023-01-19T13:27:57Z | Active Committers: []
	 -  Repository: exercise-remove-commit-history | GHAS Status: False | Last Pushed At: 2023-01-19T13:31:20Z | Active Committers: []
	 -  Repository: ghas-devtraining-gusshawstewart | GHAS Status: False | Last Pushed At: 2023-02-03T13:11:39Z | Active Committers: []
	 -  Repository: go-gin-example | GHAS Status: False | Last Pushed At: 2023-07-03T08:59:02Z | Active Committers: []
	 -  Repository: rails-ex | GHAS Status: False | Last Pushed At: 2023-03-03T16:00:58Z | Active Committers: []
	 -  Repository: rails-react-typescript-docker-example | GHAS Status: False | Last Pushed At: 2023-03-10T12:15:50Z | Active Committers: []
	 -  Repository: python-twilio-example-apps | GHAS Status: False | Last Pushed At: 2023-02-21T11:14:38Z | Active Committers: []
	 -  Repository: fibonacci-webapp-benchmark | GHAS Status: False | Last Pushed At: 2023-02-22T15:33:22Z | Active Committers: []
	 -  Repository: terraform-test | GHAS Status: False | Last Pushed At: 2023-02-23T11:46:53Z | Active Committers: []
	 -  Repository: auth0-golang-web-app | GHAS Status: False | Last Pushed At: 2023-02-28T08:59:47Z | Active Committers: []
	 -  Repository: webapp-go | GHAS Status: False | Last Pushed At: 2023-02-28T08:59:43Z | Active Committers: []
	 -  Repository: sysfoo | GHAS Status: False | Last Pushed At: 2023-03-01T08:26:30Z | Active Committers: []
	 -  Repository: WebApp | GHAS Status: False | Last Pushed At: 2023-03-01T08:27:14Z | Active Committers: []
	 -  Repository: WebApplicationSkeleton | GHAS Status: False | Last Pushed At: 2023-03-01T08:26:38Z | Active Committers: []
	 -  Repository: micro-frontend-example | GHAS Status: False | Last Pushed At: 2023-03-01T08:40:34Z | Active Committers: []
	 -  Repository: serverless-web-app-example | GHAS Status: False | Last Pushed At: 2023-03-01T08:40:38Z | Active Committers: []
	 -  Repository: react-redux-example | GHAS Status: False | Last Pushed At: 2023-03-01T08:54:02Z | Active Committers: []
	 -  Repository: scan-public-actions | GHAS Status: False | Last Pushed At: 2023-03-14T11:36:51Z | Active Committers: []
	 -  Repository: msdocs-python-flask-webapp-quickstart | GHAS Status: False | Last Pushed At: 2022-11-05T01:52:32Z | Active Committers: []
	 -  Repository: imagebird | GHAS Status: False | Last Pushed At: 2023-03-02T15:48:07Z | Active Committers: []
	 -  Repository: python-desktop-examples | GHAS Status: False | Last Pushed At: 2023-03-02T16:30:12Z | Active Committers: []
	 -  Repository: python-geeks | GHAS Status: False | Last Pushed At: 2023-03-02T15:53:00Z | Active Committers: []
	 -  Repository: Scheduling-App | GHAS Status: False | Last Pushed At: 2023-03-06T10:22:59Z | Active Committers: []
	 -  Repository: python-ecommerce | GHAS Status: False | Last Pushed At: 2023-03-02T16:33:00Z | Active Committers: []
	 -  Repository: wechat_jump_game | GHAS Status: False | Last Pushed At: 2023-03-02T16:36:18Z | Active Committers: []
	 -  Repository: uvicorn-poetry | GHAS Status: False | Last Pushed At: 2023-03-03T12:02:05Z | Active Committers: []
	 -  Repository: sandcage-api-python | GHAS Status: False | Last Pushed At: 2023-03-03T12:07:41Z | Active Committers: []
	 -  Repository: braintree_rails_example | GHAS Status: False | Last Pushed At: 2023-03-03T16:04:44Z | Active Committers: []
	 -  Repository: vulnerable-app | GHAS Status: False | Last Pushed At: 2018-02-07T12:02:03Z | Active Committers: []
	 -  Repository: vulnerable-node | GHAS Status: False | Last Pushed At: 2023-07-27T11:09:36Z | Active Committers: []
	 -  Repository: vulnerable-node-2 | GHAS Status: False | Last Pushed At: 2023-04-12T13:30:17Z | Active Committers: []
	 -  Repository: central-config | GHAS Status: False | Last Pushed At: 2023-07-24T13:36:49Z | Active Committers: []
	 -  Repository: test-public | GHAS Status: False | Last Pushed At: 2023-10-11T12:39:53Z | Active Committers: []
----------------------------------------
# Maximize coverage with additional licenses 

**Turning GHAS on following repositories will consume 1 additional licenses**
- Combination of repositories to activate GHAS on:
	 -  Repository: hilly | GHAS Status: False | Last Pushed At: 2023-11-01T11:43:43Z | Active Committers: ['hill-scribes-0x', 'theztefan']

 New active comitters that will consume GHAS license:
	 -  hill-scribes-0x
----------------------------------------
# End state coverage 

Total repositories with GHAS: 47
Coverage: 100.0%
