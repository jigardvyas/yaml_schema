.PHONY: all check validate_yaml validate_schema

ifneq "$(VIRTUAL_ENV)" ""

all: check

check: validate_yaml validate_schema

validate_yaml: 
	@echo "*****************************************************"
	@echo Running yaml load against all candidate yaml files
	@echo "*****************************************************"
	@./.travis/validate_yaml.py

validate_schema: 
	@echo "*****************************************************"
	@echo Running schema check against all candidate yaml files
	@echo "*****************************************************"
	@./.travis/validate_schema.py

endif
