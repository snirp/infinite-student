#! /usr/bin/env node

/*<
# This code file follows the SLiP (Semi-Literate Programming) annotation convention.
# specification at: ...
title:      "Just a test file"
author:     Roy Prins
published:  17-04-2014
status:     project
progress:   90
summary: >
    Does javascript render correctly?
>*/

/*<
#Markdown section

This is just plain old markdown
 >*/

var Q = require('q');
var _ = require('lodash');
var path = require('path');
var prog = require('commander');

var pkg = require('../package.json');
var generators = require("../lib/generate").generators;
var fs = require('../lib/generate/fs');

var utils = require('./utils');
var build = require('./build');

// General options
prog
.version(pkg.version);

var buildCommand = function(command, action) {
    return command
    .option('-o, --output <directory>', 'Path to output directory, defaults to ./_book')
    .option('-f, --format <name>', 'Change generation format, defaults to site, availables are: '+_.keys(generators).join(", "))
    .option('-t, --title <name>', 'Name of the book to generate, defaults to repo name')
    .option('-i, --intro <intro>', 'Description of the book to generate')
    .option('-g, --github <repo_path>', 'ID of github repo like : username/repo')
    .option('--githubHost <url>', 'The url of the github host (defaults to https://github.com/')
    .option('--theme <path>', 'Path to theme directory')
    .action(action);
}

/*<
#Markdown section 2

This is just plain old markdown. This is just plain old markdown. This is just plain old markdown. This is just plain old markdown. This is just plain old markdown.
This is just plain old markdown. This is just plain old markdown. This is just plain old markdown. This is just plain old markdown.
 >*/

buildCommand(prog
.command('build [source_dir]')
.description('Build a gitbook from a directory'), build.folder);

/*
regular
multiline
comment
 */

buildCommand(prog
.command('serve [source_dir]')
.description('Build then serve a gitbook from a directory')
.option('-p, --port <port>', 'Port for server to listen on', 4000),
function(dir, options) {
    build.folder(dir, options)
    .then(function(_options) {
        console.log();
        console.log('Starting server ...');
        return utils.serveDir(_options.output, options.port)
        .fail(utils.logError);
    })
    .then(function() {
        console.log('Serving book on http://localhost:'+options.port);
        console.log();
        console.log('Press CTRL+C to quit ...');
    });
});

/*<
#Markdown section 3

This is just plain old markdown. This is just plain old markdown. This is just plain old markdown. This is just plain old markdown. This is just plain old markdown.
This is just plain old markdown. This is just plain old markdown. This is just plain old markdown. This is just plain old markdown.
 >*/