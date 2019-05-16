// Chainbot functions

// start game
function startGame()
{
    if (!$("#game-start-btn").hasClass("disabled")) {
        $("#game-status").load("/control/gbegin");
        setTimeout(function(){
            window.location.reload(true);
        });
    }
}

// stop game
function stopGame()
{
    if (!$("#game-stop-btn").hasClass("disabled")) {
        $.ajax({
            method: "GET",
            url: "/control/gend"
        });
    }
}

// check whether game can be started
function canStartGame()
{
    $.ajax({
        method: "GET",
        url: "/status/can_start",
        success: function(result) {
            if (result.status == "ok") {
                if (result.can_start) {
                    $("#game-start-btn").removeClass("disabled");
                }
                else {
                    $("#game-start-btn").addClass("disabled");
                }
            }
        }});
}

// start refreshing view
var refreshTimer;
function startRefreshing()
{
    // refresh immediately
    refreshStatus();
    refreshTimer = setInterval(refreshStatus, 1000);
}

// stop refreshing view
function stopRefreshing()
{
    clearInterval(refreshTimer);
}

// perform full refresh of view
var currentGameStatus;
function refreshStatus()
{
    getPlayerNames();
    $.ajax({
        method: "GET",
        url: "/status/game",
        success: function(result) {
            if (result.status == "ok") {
                // update status globally
                currentGameStatus = result.game;
                if (result.game != "stopped") {
                    // set scores
                    $.each(result.scores,
                           function(key, val) {
                               if (key != "status") {
                                   setScore(key, val, result.serving);
                               }
                           });
                    // enable pause/stop
                    $("#game-stop-btn").removeClass("disabled");
                    $("#game-pause-btn").removeClass("disabled");
                    $("#game-start-btn").addClass("disabled");
                    // disable dropdown in player names
                    var p;
                    for (p=0;p<4;p++) {
                        $("#pline-"+p+"-drop").addClass("disabled");
                    }
                }
                else {
                    var p;
                    for (p=0; p<4; p++) {
                        disableControls(p);
                        // enable dropdowns in player names
                        $("#pline-"+p+"-drop").removeClass("disabled");
                    }
                    $("#game-stop-btn").addClass("disabled");
                    $("#game-pause-btn").addClass("disabled");
                    canStartGame();
                }
            }
        }
    });
}

// retrieve current player names
function getPlayerNames() {
    $.ajax({
        method: "GET",
        url: "/status/players",
        success: function(result) {
            $.each(result, function(key, val) { $("#pline-"+key).text(val.web_txt); });
        }});
}


// refresh score in view
function setScore(player, score, serving)
{
    if (serving != player) {
        $("#pline-"+player).removeClass("btn-danger");
    }
    else
    {
        $("#pline-"+player).addClass("btn-danger");
    }

    $("#pscore-"+player).text(score);
}

// set turn manually
function setTurn(playerNum)
{
    $.ajax({
        method: "GET",
        url: "/debug/setturn/"+playerNum
    });
}


// trigger a scoring event
function scoringEvt(playerNum, evtType)
{
    $.ajax({
        method: "GET",
        url: "/control/scoreevt/"+playerNum+","+evtType
    });
}

// disable referee controls for player
function disableControls(playerNum)
{
    var evt;
    for (evt = 0; evt < 8; evt++) {
        $("#p"+playerNum+"Evt"+evt).addClass("disabled");
        $("#scoreDropdownBtn"+playerNum).addClass("disabled");
    }
}


// enable referee controls for a player
function enableControls(playerNum)
{
    var evt;
    for (evt = 0; evt < 8; evt++) {
        $("#p"+playerNum+"Evt"+evt).removeClass("disabled");
        $("#scoreDropdownBtn"+playerNum).removeClass("disabled");
    }
}

// handle click on player button
function pnameClick(playerNum) {
    if (currentGameStatus == "stopped") {
        // add or remove player etc

    } else {
        // set turn
        $.ajax({method: "GET", url: "/debug/setturn/"+playerNum});
    }
}

function addPlayer(playerNum, username) {

}
function rmPlayer(playerNum) {}
function pairRemote(playerNum) {}


// update local registry
function updateRegistry() {
    $.ajax({method: "GET", url: "/persist/update"});
}
