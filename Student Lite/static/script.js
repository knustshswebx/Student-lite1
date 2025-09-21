document.addEventListener("DOMContentLoaded", function(){
    const subjectSelect = document.getElementById("subject");
    if(subjectSelect){
        subjectSelect.addEventListener("change", function(){
            const historyDiv = document.getElementById("historyCountryDiv");
            if(historyDiv){
                historyDiv.style.display = (this.value==="History")?"block":"none";
            }
        });
    }
});
