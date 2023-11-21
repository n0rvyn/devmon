#!/bin/bash


#for f in $(find ../devlist -type f -name "*.yaml" -print); do
#  grep -E "explanation|related_symbol|arith_symbol|arith_pos:|id|id_range" $f
#done

find ../devlist -type f -name "*.yaml" \
  -exec grep -E "explanation:|related_symbol:|arith_symbol:|arith_pos:| id:| id_range:|OIDs|entry" {} \;

function receive_confirmation() {
  read -r -p "$1 [y/N] " response

  if [[ ! $response  =~ ^([yY][eE][sS]|[yY])$ ]]; then
    return 1
  fi

  return 0
}


if ! receive_confirmation "Midify the keys:"; then
  exit 0
fi

if [ $(uname -s) == 'Darwin' ]; then
  find ../devlist -type f -name "*.yaml" \
	  -exec sed -i "" 's/explanation:/description:/g' {} \; \
	  -exec sed -i "" 's/related_symbol:/read_name_from:/g' {} \; \
	  -exec sed -i "" 's/arith_symbol:/read_arith_value_from:/g' {} \; \
	  -exec sed -i "" 's/arith_pos:/arith_position:/g' {} \; \
	  -exec sed -i "" 's/ id:/ table:/g' {} \; \
	  -exec sed -i "" 's/ id_range:/ table:/g' {} \; \
	  -exec sed -i "" 's/OIDs:/entries:/g' {} \; \
	  -exec sed -i "" 's/entry:/entries:/g' {} \; \

elif [ $(uname -s) == 'Linux' ]; then
  find ../devlist -type f -name "*.yaml" \
	  -exec sed -i 's/explanation:/description:/g' {} \; \
	  -exec sed -i 's/related_symbol:/read_name_from:/g' {} \; \
	  -exec sed -i 's/arith_symbol:/read_arith_value_from:/g' {} \; \
	  -exec sed -i 's/arith_pos:/arith_position:/g' {} \; \
	  -exec sed -i 's/ id:/ table:/g' {} \; \
	  -exec sed -i 's/ id_range:/ table:/g' {} \; \
	  -exec sed -i 's/OIDs:/entries:/g' {} \; \
	  -exec sed -i 's/entry:/entries:/g' {} \; \

else
  echo "Platform not supported."
fi

