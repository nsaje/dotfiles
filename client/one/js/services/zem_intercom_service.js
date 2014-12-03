/*globals Intercom*/
"use strict";


/**
   window.Intercom('boot', {
              app_id: "ixc9vxvs",
              // TODO: The current logged in user's full name
              name: "John Doe",
              // TODO: The current logged in user's email address.
              email: "john.doe@example.com",
              // TODO: The current logged in user's sign-up date as a Unix timestamp.
              created_at: 1234567890
        });  
        window.Intercom('update');   

*/
oneApp.factory("zemIntercomService", function() {
    var INTERCOM_APP_ID = 'ixc9vxvs';

    function boot(user) {
        Intercom('boot',{
              app_id: INTERCOM_APP_ID,
              name: ,
              email: user.email,
        });
        
    }

    function update() {
        Intercom('update');
    }


    return {
        boot: boot,
        update: update
    };
});
