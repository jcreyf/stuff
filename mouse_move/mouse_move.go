package main

/*
	Little app to move the mouse pointer every so many seconds to avoid the screensaver from kicking in.
	The number of seconds is configurable through a config yaml-file and the app will dynamic detect
	config changes and will apply them on the fly during runtime so that the app does not need to get
	bounced for new settings to take effect.

	Some temp quick notes:
		export GOPATH=/Users/JCREYF/data/development/go/externals

		go get github.com/go-yaml/yaml
			-> /Users/JCREYF/data/development/go/externals/src/github.com/go-yaml/
	or
		go get gopkg.in/yaml.v3
			-> /Users/JCREYF/data/development/go/externals/src/gopkg.in/yaml.v3/

*/

import (
	"fmt"
	"io/ioutil" // Needed to read the YAML config-file
	"os"
	"os/signal" // Needed to detect SIGINT and handle it
	"reflect"   // Needed to scan through the appConfig and set default values
	"strconv"   // Needed to convert appConfig default values from string to integers or boolean
	"syscall"
	"time"

	"github.com/go-vgo/robotgo" // Needed to move the cursor
	"gopkg.in/yaml.v3"          // Needed to parse YAML config
)

var config *appConfig = nil
var configFileStat os.FileInfo = nil

/*
	Structure of the application's yaml configuration file.
	We are using tags on the struct fields to set default values.
	(see about YAML stuff: https://github.com/go-yaml/yaml/tree/v3.0.1)
*/
type appConfig struct {
	//	Config struct {
	Enabled      bool  `yaml:"enabled" default:"true"`
	Debug        bool  `yaml:"debug" default:"false"`
	DelaySeconds int64 `yaml:"delay_seconds" default:"60"`
	//	}
}

/*
	Function to scan through the configuration structure and see if we got
	values for all fields.  If not, then see if we have a "default value" tag
	on the field and use it.
*/
func setDefaults(ptr interface{}, tag string) error {
	if reflect.TypeOf(ptr).Kind() != reflect.Ptr {
		return fmt.Errorf("Not a pointer")
	}
	v := reflect.ValueOf(ptr).Elem()
	logDebug(fmt.Sprintln(v))
	t := v.Type()
	logDebug(fmt.Sprintln(t))
	logDebug(fmt.Sprintf("fields: %v", t.NumField()))
	for i := 0; i < t.NumField(); i++ {
		logDebug(fmt.Sprintf("field: %v:", t.Field(i).Name))
		logDebug(fmt.Sprintf("  -> value: %v", t.Field(i)))
		logDebug(fmt.Sprintf("  -> type: %v", t.Field(i).Type))
		logDebug(fmt.Sprintf("  -> tags: %v", t.Field(i).Tag))
		logDebug(fmt.Sprintf("  -> default: %v", t.Field(i).Tag.Get(tag)))
		// if defaultVal := t.Field(i).Tag.Get(tag); defaultVal != "-" {
		if defaultVal := t.Field(i).Tag.Get(tag); defaultVal != "" {
			if err := setFieldDefaultValue(v.Field(i), defaultVal); err != nil {
				return err
			}
		} else {
			logDebug(fmt.Sprintf("Field '%v' has no default value", t.Field(i).Name))
		}
	}
	return nil
}

/*
	The setDefaults() function calls this method for each field for which we don't have
	a config value and for which we can set a default value.
*/
func setFieldDefaultValue(field reflect.Value, defaultVal string) error {
	logDebug(fmt.Sprintf("  setField: %v (%v) -> %v", field, field.Kind(), defaultVal))
	if !field.CanSet() {
		return fmt.Errorf("Can't set value\n")
	}
	switch field.Kind() {
	case reflect.Int, reflect.Int64:
		logDebug("   INT")
		if val, err := strconv.ParseInt(defaultVal, 10, 64); err == nil {
			field.Set(reflect.ValueOf(int(val)).Convert(field.Type()))
		}
	case reflect.String:
		logDebug("   STRING")
		field.Set(reflect.ValueOf(defaultVal).Convert(field.Type()))
	case reflect.Bool:
		logDebug("   BOOL")
		//		if val, err := strconv.ParseBool(defaultVal); err == nil {
		//			field.Set(reflect.ValueOf(val).Convert(field.Type()))
		//		}
		val, err := strconv.ParseBool(defaultVal)
		if err != nil {
			log(fmt.Sprintln(err))
		}
		field.Set(reflect.ValueOf(val).Convert(field.Type()))
	}
	return nil
}

/*
	Read and parse the config yaml-file:
	example file:
		config:
		  enabled: true
		  debug: true
		  delay_seconds: 10
*/
func readConfig(filename string) (*appConfig, error) {
	yamlFile, err := ioutil.ReadFile(filename)
	if err != nil {
		return nil, err
	}
	// config := &appConfig{}
	config = &appConfig{}
	// Apply default values on fields in the structure for which we don't have a value for in the yaml:
	setDefaults(config, "default")
	// Now parse the structure:
	err = yaml.Unmarshal(yamlFile, config)
	if err != nil {
		// return nil, fmt.Errorf("in file %q: %v", filename, err)
		log(fmt.Sprintf("in file %q: %v", filename, err))
		os.Exit(1)
	}
	return config, nil
}

/*
	Move the mouse pointer just a little to trick the system in believing there is user
	activity.
*/
func moveMouse() {
	if config.Enabled {
		// https://github.com/go-vgo/robotgo/blob/master/docs/doc.md
		x, y := robotgo.GetMousePos()
		logDebug(fmt.Sprintf("Moving Mouse: (x:%v, y:%v)", x, y))
		robotgo.MoveMouse(x+1, y+1)
		robotgo.MoveMouse(x, y)
		//	robotgo.Click()
	} else {
		logDebug("Not running (config.enabled == false)")
	}
}

func logConfigFileInfo() {
	log(fmt.Sprintf("Config (%v):", configFileStat.ModTime().Format("01-02-2006 15:04:05")))
	log(fmt.Sprintf("  Enabled: %v", config.Enabled))
	log(fmt.Sprintf("  Debug: %v", config.Debug))
	log(fmt.Sprintf("  Delay seconds: %v", config.DelaySeconds))
}

/*
	Sleep for a number of seconds (configured in config-file).
*/
func wait() {
	logDebug("sleep...")
	time.Sleep(time.Duration(config.DelaySeconds) * time.Second)
}

func log(text string) {
	fmt.Printf("%v: %v\n", time.Now().Format("01-02-2006 15:04:05"), text)
}
func logDebug(text string) {
	if config.Debug {
		log("DEBUG: " + text)
	}
}

func main() {
	var err error = nil
	var configFile string = "mouse_move.yaml"

	// Set a SIGINT (CRTL-C) handler:
	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-c
		log("End of app")
		os.Exit(1)
	}()

	// Read the app's config file:
	config, err = readConfig(configFile)
	if err != nil {
		log(fmt.Sprintln(err))
	}

	// Get some stats of the config-file so that we have something to detect file changes
	// while the app is running:
	configFileStat, err = os.Stat(configFile)
	if err != nil {
		log(fmt.Sprintln(err))
	}
	// Log the configuration settings:
	logConfigFileInfo()

	/*
		Go in an endless loop here, looping through:
			1. move the mouse pointer;
			2. wait the configured number of seconds;
			3. see if yaml-file changed:
				- if yes, then reload it and use the new config values;
				- if "enabled" is now set to false, then stop moving the mouse pointer;
	*/
	for {
		moveMouse()
		wait()
		// Check to see if the config-file changed:
		_configFileStat, err := os.Stat(configFile)
		if err != nil {
			log(fmt.Sprintln(err))
		}
		if _configFileStat.Size() != configFileStat.Size() || _configFileStat.ModTime() != configFileStat.ModTime() {
			log("THE CONFIG-FILE CHANGED DURING RUNTIME!!!")
			log("Reloading and applying the new configuration...")
			// Re-read the app's config file to update the settings at runtime:
			config, err = readConfig(configFile)
			configFileStat = _configFileStat
			logConfigFileInfo()
		}
	}
}
