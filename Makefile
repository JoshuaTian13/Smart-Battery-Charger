CXX ?= c++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -Werror -pedantic
PYTHON ?= python3

BUILD_DIR := build
FIRMWARE_TEST := $(BUILD_DIR)/charger-controller-test

.PHONY: test firmware-test python-test clean

test: firmware-test python-test

firmware-test: $(FIRMWARE_TEST)
	./$(FIRMWARE_TEST)

$(FIRMWARE_TEST): firmware/src/charger_controller.cpp firmware/test/charger_controller_test.cpp
	mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -Ifirmware/include $^ -o $@

python-test:
	$(PYTHON) -m unittest discover -s cloud/tests -p 'test_*.py'
	$(PYTHON) -m unittest discover -s ml/tests -p 'test_*.py'

clean:
	rm -rf $(BUILD_DIR) cloud/**/__pycache__ ml/**/__pycache__
